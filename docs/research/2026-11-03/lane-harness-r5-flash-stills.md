# Lane harness-r5-flash-stills: an L3 renderer for the Flash menus (2026-11-03)

Why: the System page's Settings and Load views took four in-game passes today because `frame_stills` draws a mock,
not the movie. Route 0010: an open tool first, Ruffle (MIT OR Apache-2.0; owner approved the fetch in session).

## What was built
- Ruffle nightly-2026-11-03: the desktop tarball's sha256 `26269a23…1c97` matches the release page digest. The
  release ships no exporter, so `tools/ui_theme/ruffle/build_exporter.sh` builds it from the tag's source (it needs
  Rust and Java, ~10 min cold) with `exporter-argonia.patch`. The patch makes two changes: AVM traces go to stderr,
  and local fetches turn Scaleform's `\` paths into `/` and are case-blind. The binary lives in
  `~/.argonia/tools/ruffle`. Ruffle has its row in the sourcing register.
- `tools/ui_theme/avm1.py` is a small AS2 bytecode assembler. `tools/ui_theme/flash_still.py` appends root frames to
  a copy of the movie and makes the engine's calls itself (InitExtensions, RestoreSavedSettings(2), startPage, then
  StartState(3) or the save list plus onSaveLoadBatchComplete). It stages a case-blind union of the stack's interface
  folders, so the movie's ImportAssets2 and its run-time loadMovie of the BG art resolve. It serves gfxfontlib from
  our Pelagiad library and puts `$KEY` text through translate_english.txt and the translations. It checks that the
  capture frame actually ran, by a trace. A second render with every text field hidden gives a text mask, and from
  it each item's ink, ground and WCAG contrast. Each render takes about 1.5 s.
- `python -m tools.ui_harness menus --flash [--theme <overlay>]` renders quest_journal system-main, system-settings
  and system-load. Any text item under contrast 2.0 fails. `docs/loops.md` has the new line.

## Faithfulness (pre-fix = retheme at e57e1e4a^, fixed = HEAD; both rebuilt from the stack's Dear Diary + Wood and Paper)
The measure on the pre-fix build: list rows, Level and footer labels have ink #000000 on #0d150f, contrast 1.13.
There are 26 fails. The measure on the fixed build: the same items are #e5dbb1, contrast 13.35, with 0 fails. The
dimmed category rows are 4.83 in both.

A reader compared the renders with the in-game stills 09-system-settings and 11-system-load (batch 20261103T170644).
The pre-fix render shows exactly the black-on-dark items the game showed, and no item's colour differs from the
game. In the fixed render every text item is cream. The art matches the game: the frame, the footer box, the Level
flourishes and bar.

The renderer also found a defect the game stills already held. The footer's button glyphs (Tab/X/T, in game B/X/Y)
stay near-black in the fixed build too. They are button art, not text fields, so the contrast mask misses them.
This needs a retheme follow-up.

## What it cannot show
- The Scaleform-only extras: filters and blend modes that Ruffle draws differently, the fonts' hinting, the
  tab-label font (its translated glyphs fall back to a device face).
- The engine's data. Our sample entries stand in for real saves and settings rows (the game had 5 settings rows and
  11 saves with a scrollbar; the render has 3 and 7, no scrollbar), the real date, the real version and the level.
- The things other mods do at run time. The game hides the tab row and shows gamepad glyphs; the render keeps the
  tabs and shows PC keys.
- The game world behind the menu: the render's ground is flat #333.
- Only quest_journal's System states are driven. Each other retinted movie needs its own state recipe in `STATES`.
- The in-game still still closes the check (L4).

## Rebuild (nothing lives only on this machine)
Only the binary is kept: `~/.argonia/tools/ruffle/bin/ruffle-exporter` (sha256 7ac01e3c…dc0a) and `exporter.commit`.
The source tree and the Rust toolchain were deleted (nothing else in the repo uses cargo). To rebuild, check out
Ruffle tag `nightly-2026-11-03`, apply `tools/ui_theme/ruffle/exporter-argonia.patch`, then run
`cargo build --release -p exporter`. Rust and Java (openjdk-21-jre-headless) must be installed.
`tools/ui_theme/ruffle/build_exporter.sh` does all of that and deletes the source tree afterwards.
