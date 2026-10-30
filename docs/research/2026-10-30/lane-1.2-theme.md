# Lane 1.2-theme: Pelagiad everywhere, the light retheme, the title (report)

Dated 2026-10-30. Chunk 1.2 §a, the build-VM side. Test level L3. Route: our own SWF and DDS writers, run at install
(0014 §7–8). This report holds the evidence; the reasoning and the dead ends are in `docs/research/journals/ui.md`.

## What was delivered

| Deliverable | Where | Measured on the build VM |
|---|---|---|
| Font library + fontconfig | `tools/ui_theme/fontlib.py`, `swf.py` | 274 glyphs, `fonts_pelagiad.swf` 40 KB, 17 maps; 0 unmapped imports across the dear-diary, skyui, wood-and-paper and oblivion-loading-menu folders; peak 41 MB |
| Retheme recipe | `tools/ui_theme/retheme.py`, `palette.py` | 44 files, 44 bitmaps on the laid mods, 0 warnings; 6.9 s; peak 277 MB |
| Title | `ui/title/title.py` (source), `ui/title/argonia-title.svg` (generated, committed) | wallpaper 2048² DXT1, made at install |
| L3 stills | `tools/ui_theme/stills.py` → `out/ui_theme/stills/` | before and after of the main menu and the inventory; bitmap contact sheet; loading menu |
| Install steps | `installer/steps/ui-theme.md` | |
| L4 draft | `tests/journeys/ui-sweep.yaml` | owed to a game lane |
| Pins and sourcing | `py:fonttools=4.60.1` in `toolchain.lock`; fontTools row; Pelagiad and Dear Diary rows' `used_by` in `data/sourcing-register.json` | |
| Tests | `tools/ui_theme/tests/test_ui_theme.py` | 8 passed, 0.3 s (synthetic fixtures only) |

## Deviations from the brief

- **The art is in SWFs, not DDS.** Dear Diary draws its frames from DefineBitsLossless2 bitmaps in
  `interface/deardiary/**/*_BG.swf`, so the recipe recolours those bitmaps and writes new SWFs. The only DDS is the
  main-menu wallpaper, and it is Skyrim's map with the "Skyrim" wordmark painted in. Our title wallpaper replaces it
  whole: our own procedural paper, with no source image.
- **Two Nordic watermarks are cleared**, not recoloured:
  - the horned Dragonborn helmet, on the map's side panel (`map_bonus_BG.swf`);
  - Skyrim's barbed enchanting sigil (`craftingmenu_enchanting_BG.swf`).

  Each is checked against its measured size, so a changed Dear Diary version warns and exits 1.
- **Script fonts.** `$DragonFont` and `$FalmerFont` map to Daedric (0006). `$ConsoleFont` stays vanilla Arial.

## Reader (L3)

- Round 1: FAIL. The title was clipped and the header cut off by the mock's panel. The bright loading parchment
  stood off-palette. The reader thought the backdrop might be a ghost of the map; it is procedural noise. The
  helmet and the sigil were already gone.
- Fixes: the panel was moved and the text shrunk. The palette's top stop was held at `--paper`.
- Round 2: **PASS** on all six checks: warm paper, moss frames, no Skyrim map or wordmark, a non-Nordic ornament,
  no Nordic mark in any bitmap, and legible text.
- Polish left (P2 rolling):
  - a faint red hairline on the favourites sheets;
  - orange speckle at the loading frame's corners;
  - the main-menu backdrop is plain brown (a moss cast is optional);
  - the teal alchemy flask watermark;
  - the near-black wood of the MCM sheet;
  - Pelagiad's uncial capitals (D reads close to P).

## Gone list: gaps for the game lane (stack.py is not edited here)

- **No Google Maps.** Present: `data/dependencies.json` row `no-google-maps` (profile play, chunk 1.4), at line 34
  of the laid modlist.
- **`bShowQuestMarkers` and `bShowCompass` are missing.** Neither is set anywhere:
  - no dependency row has an `ini` edit for them;
  - `stack.py` writes no Skyrim.ini or SkyrimPrefs.ini to the profile (`apply_ini`, `infra/gpu-box/stack.py:503`,
    edits only files inside mods).

  The game lane is owed an `[Interface]` edit setting both to 0 in the profile's own SkyrimPrefs.ini.
- **The compass in the router.** `data/router/surfaces.json` has `hudCompass` and `hudQuestMarkers` suppressed
  through the `hudElements` hook. Its mechanism is marked UNVERIFIED, and its text relies on the ini settings above.
  It is unproven until L4.

## Owed

- **L4:** run `tests/journeys/ui-sweep.yaml` on the game machine (needs the installer step run there). The first
  still proves whether Scaleform accepts our DefineFont3.
- **Install order:** 3.4 adds `argonia-theme` above the three Dear Diary-family mods.

## Reproduce

```
M=~/.argonia/stack/MO2/mods; F=~/argonia-private/fonts/pelagiad/Pelagiad.ttf; P=~/.argonia/venv/bin/python
$P -m tools.ui_theme.fontlib --ttf $F --out out/ui_theme/fonts --check $M/dear-diary $M/skyui $M/wood-and-paper $M/oblivion-loading-menu
$P -m tools.ui_theme.retheme --mods $M/dear-diary $M/wood-and-paper $M/oblivion-loading-menu --ttf $F --out out/ui_theme/argonia-theme
$P -m tools.ui_theme.stills --mods $M/dear-diary $M/wood-and-paper --theme out/ui_theme/argonia-theme --fontlib out/ui_theme/fonts/interface/fonts_pelagiad.swf --out out/ui_theme/stills
```
