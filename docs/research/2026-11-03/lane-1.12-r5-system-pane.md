# Lane 1.12-r5-system-pane

Owner ruling (#37, 2026-11-03 08:55): the System pane is styled like the in-game menu views, never paper. Coordinator ruling: (b), judged against the dialogue window and the Wind UI retint.

Why the stand-ins are paper: ui/views/{inventory,charsheet,magic} are round-4 HTML stand-ins in the paper theme (render.ts:63 / :69 `window paper`); the player meets Wind UI's dark frame inventory (1.12 table rows 113-122), so they are not what the player sees and were left untouched.

## Cause and change
- ui/views/system/system.css kept a paper `.sheet` with ink, rust and moss entries (round 4, commit 173afbdd). Now the sheet is a `--frame-well` panel; heads, entries, hover/focus and the dimmed entry use the `--frame-*` tokens of ui/views/core/theme.css; the window ground is `var(--frame-ground)` (was a hard-coded colour). render.ts and main.ts unchanged.
- docs/phases/1-core-loop/1.12-the-in-game-ui.md:118: System pane row reads "our frames (in-game menu style; never paper, owner 2026-11-03)". Paper rows remain: main menu / load / new game, books, the journal.

## Measured (menu loop, 12 runs, 0 fails)
Lowest contrast in the System pane: 6.61:1 before (paper), 10.88:1 after; the dimmed Load entry computes 6.97:1.

## Reader (System vs dialogue, 1080p and v5-unfolded)
PASS on frame, ground, trim, text, headings, focus, no paper. Gaps (low priority, not done): System focus row lacks the dialogue's orange top/bottom bars; System title is left-aligned and has no corner marks.

## Owed
checks.md row (L4 owed): the System pane in game beside the Wind UI inventory, one still each; journey menus-look (esc-system step), run by the planner. Question for the owner: the journal stays paper as ruled 2026-10-31 unless told otherwise.
