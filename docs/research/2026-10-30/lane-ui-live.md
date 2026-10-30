# Lane ui-live: our four views bound to PrismaUI, and the 1.2 §0 probe (report)

Dated 2026-10-30. Chunk 1.2 §0. Test level: L2 now; the L4 probe belongs to the game lane.

## Done

| Piece | Where | Proof |
|---|---|---|
| The host's rules: ops for PrismaUI, the journal-key latch, the chart's remembered view, the journal's state, the 300-topic probe window | `skse/core/{include/argonia/core,src}/views.*`, `tests/test_views.cpp` | core.views L2 green on GCC and MSVC (31/31 ctest) |
| The binding | `skse/ArgoniaCore/src/views.cpp` and `prisma_api.h` (our declaration of PrismaUI 1.5.1's published API) | `skse_build.sh build windows-dev` gives SKSE-BUILD OK; `ArgoniaCore.dll` is 1 668 608 bytes |
| The router wiring | the dialogue intercept pushes, then the view opens; `journalMenu` is replaced only after the "Journal" user event (J, pad Back), so Escape's System tab passes; `mapMenu` opens our chart; the HUD is always on (`hud.state` at game ready, `hud.bars` on change, 5 Hz); sitting and dialogue close through `CloseView` | MSVC green |
| Intents | JS `argoniaIntent` goes to an SKSE task, then to `ViewIntent`; `view.close` covers dialogue, journal and chart; `journal.page` re-pushes; `chart.pan` writes `ArgoniaUI-chart.json` beside the SKSE logs | L2 (Host); L4 owed |
| Dev reads | `core ViewProbe <n>` and `core Views` (bridge whitelist plus `tools/bridge.py`'s mirror) | test_bridge_call |
| Views | `bridge.ts`: the `window.argoniaPush` alias (InteropCall resolves only top-level names). `nav.ts`: PrismaUI's pad events. `dialogue`: the typed topic filter | `make ui` green, with a new filter test |
| The bundle | `stack.py stage` lays `out/ui/views` as the `argonia-views` mod at `PrismaUI/views/argonia` | `python3 tools/ui_harness/build.py`: 21 files, 9.2 MB, font and chart present |
| The probe | `tests/journeys/ui-probe.yaml` | `--dry`: 21 steps, scene first-place, 4 kept values: ok |
| The choice, ready to fill | decision 0017, "1.2 §0 record" | |
| The dependency row | `prismaui`: the runtime corrected (the archive carries `PrismaUI.dll`), and the link through our API declaration recorded | |

## Calls made

- **The map is our chart view, not FWMF.** Three reasons, written in 0017:
  - C9: the vanilla map draws the player's marker;
  - the revealed layer is per cell;
  - one input model for all the screens.

  FWMF stays laid. Without PrismaUI the handler is never registered and M opens FWMF's map.
- **Window layout is per install, not per save.** Morrowind keeps its layout in its ini. Our layout is a settings
  file read on every opening, not a co-save family.
- **Pelagiad may ship.** It is OFL, which allows redistribution with its licence (0017 §5: "import"). The bundle is
  still made at install (0014), since the chart layers in it are derived.

## Owed (named, not done)

1. **A `relaunch` action in `tools/run_journey.py`** (`Bridge.launch`, then `apply_scene`). Until it exists, the
   journey's `relaunch` and `remembered` steps are `owed`. The game lane can relaunch by hand between `chart-reopen`
   and `remembered`.
2. **The chart's revealed cells and discovered places**: a co-save family (1.2 §e). The chart shows the sketch
   only for now.
3. **The journal entry text**: the stage log lines, as a generated table into core (1.4/2.12). Entries show the
   date and the quest heading only.
4. **Hiding the vanilla HUD's bars and compass** (the router's hudBars and hudCompass rows) is 1.2 §d's. Our HUD draws
   over it.
5. **The scroll's hitch is an L5 clip.** The runner reads frame times between actions, never during them.

## Which numbers decide

From `ui-probe`:
- `bound`;
- `frames-open` p99 ≤ 22.2 ms, and the open − closed p50 ≤ 1.0 ms;
- the scroll clip, with no hitch;
- `chart-reopen` and `remembered`;
- the journal key, with Escape kept.

Scaleform only if PrismaUI does not bind on 1.7.104, or if the cost is the web view itself. The switch cost is in
0017.

## Gate

`make check`: CHECK GREEN (347 python tests in 84 s, skse 31/31, ui, plugin round trip); lint, guard and links re-run green after the doc edits.
