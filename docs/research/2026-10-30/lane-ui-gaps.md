# Lane ui-gaps (2026-10-30): the four pieces ui-live left unbuilt

Test level L2/L3. The L4 checks belong to game-10, which has been told what to deploy and what to check.

## Built

1. **The chart's revealed cells (1.2 §e).** A new co-save family, CHRT (`skse/core` `chart.h`/`chart.cpp`).
   - It holds the discovered cells as columns by x, each with a set of y. Coordinates are kept in -32768..32767.
   - It is version 1 and has a migration hook (`chart::migrations()`, empty for now).
   - It is registered in `seam::bind` and its layout is in `schema/families.json`, so `test_roundtrip` proves
     save, load, truncation, padding and reset against the layout.
   - `views::chart_state` fills `chart.state.revealed`.
   - In ArgoniaCore (`views.cpp`), a `BGSActorCellEvent` sink on the player and a pass at each load mark the
     player's cell. Only exterior cells of `ARG_Province` count (`chart::kWorldspace`).
   - `core Views` now reports `chart revealed N`.
   - The chart view already masked its revealed layer by `revealed`, so it is unchanged.
2. **Journal entry text (1.4).** `quest_gen.journal_text` writes `generated/argonia/core/journal_text.h` through
   `core_tables.render`, so `core_tables --check` keeps it current.
   - The table holds each stage's log entry (the QUST's own text), its directions and its objectives' text. It is
     keyed by `(quest_state::key(id), stage)`.
   - `journal::stage_text` and `journal::objectives` look rows up. `views::entry_text` and
     `views::entry_directions` feed `journal_state`, which now takes a directions callback: an active quest's
     index line shows the directions of its latest stage.
   - ArgoniaCore's `OpenJournal` passes both callbacks.
   - Tested on LF83 in `test_views.cpp` (`the_journal_text`).
3. **The vanilla HUD's bars and compass hidden (1.2 §d).** This goes through the router's `hudElements` hook,
   which ArgoniaCore now installs.
   - The method: `router::kHudClips` names the movie clips `Health`, `Magica`, `Stamina` and
     `CompassShoutMeterHolder` under `_root.HUDMovieBaseInstance`. ArgoniaCore sets each clip's `_visible` to false
     and removes it from the movie's `HudElements` array (`HUDElements` is tried as a fallback), so the HUD's
     mode changes never show it again.
   - It runs at every HUD Menu opening and at every load, and only while PrismaUI is bound, so the player is never
     left without bars.
   - No INI setting is written: `bShowCompass` would persist into the player's `SkyrimPrefs.ini`.
   - The mechanism text is recorded in `data/router/surfaces.json`.
   - `core Views` reports `vanilla-hud hidden h/4, k out of HudElements[, missing: ...]`.
4. **`relaunch` in `tools/run_journey.py`.** The steps:
   1. Quit with console `qqq`. A reply lost because the game went down is expected.
   2. Poll `health` for up to 60 s and record whether the quit was clean.
   3. Call `Bridge.launch()`, which kills anything left, lays the DLL and waits for the ping.
   4. Load the save given (`true` means the journey's own) and apply the journey's scene again.

   It has two fake-bridge tests. In `ui-probe.yaml` the `relaunch` and `remembered` steps are no longer owed.
   The probe also gains checks for the vanilla HUD being hidden and for revealed cells at least one.

## Found and fixed on the way

The journal's `.flow` hides overflow. One LF83 entry (954 characters) overflowed the spread on the folded V5,
and two overflowed at 1080p, so text was cut off where the player could not see it.

- **Fix:** the journal view now turns *leaves* locally (CSS columns, scrolled one spread at a time) before it asks
  ArgoniaCore for the next page.
  - Previous and Next became view-local controls (`data-ui="turn"`) that carry the page intent.
  - Going back to a page starts at its last leaf.
  - The folio reads `1 of 1, leaf 2 of 3`.
- **New L3 check:** the harness's `JOURNAL` probe, with a new `lf83` fixture holding the real stages 10–30 and an
  `lf83+turned` still. It checks that the view's leaf count equals what the text needs, that Next is offered and
  that the page's last text sits inside its last leaf.
- **Measured:** 3 leaves at 1080p, 720p and the folded V5; 2 on the unfolded V5. The full harness gave
  132 stills and 0 fails.
- **Reader:** the text is legible and continues across the leaves, nothing is clipped and the buttons are
  correct. The folio defect it found was fixed afterwards.
- **Polish (P2 rolling):** `column-fill: auto` leaves the last leaf unbalanced, for example two lines on the
  right leaf at 1080p.

## Gates

- MSVC `windows-dev` (`ARGONIA_MODDIR=C:\argonia\no-deploy`): SKSE-BUILD OK, 32/32 ctest.
  ArgoniaCore.dll is 1,696,768 bytes, left in `C:\argonia\skse\out\windows-dev`.
- `bash skse/check.sh`: 32/32.
- pytest for run_journey, core_tables and quest_gen: 34 passed.
- Node view tests: green.
- `make check`: see the commit message of the last commit.

## Owed to game-10 (L4)

1. Deploy ArgoniaCore and the views bundle.
2. Run `ui-probe` end to end, including `relaunch` and `remembered`.
3. Walk from Claywater and check that `chart revealed` grows and the chart shows the reveal.
4. Check that the LF83 journal shows the text and directions.
5. Check that the play-camera still shows no vanilla bars and no compass.

If `HudElements` is not found, the Views line says so. In that case the clips are hidden only until the next HUD
mode change, and that is the thing to report.
