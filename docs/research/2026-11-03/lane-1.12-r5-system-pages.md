# Lane 1.12-r5-system-pages: the Journal's System page (Settings, Load) in the frame style

Status: retheme shipped (03e0043e), lockpicking step fixed (dae19f13); two L4 rows owed in checks.md (the planner re-runs menus-look).

## The frame art

- The "cream ragged frame" is not another asset: it is Wood and Paper's `interface/deardiary/quest_journal/quest_journal_BG.swf`
  bitmap #14 (1036x687, DefineBitsLossless2), already in the overlay (`argonia-theme.json`: "recoloured #14 1036x687").
  FramePalette maps its ragged wood band (saturation >= 0.45, luminance < 0.28) onto `frame-trim`..`frame-trim-hi`
  (#8a8a4a..#b5a862), so the torn edge reads as a wide cream-yellow band; the recolour keeps the shape.
- The header slot bars, the bottom "Level" well and the Cancel tab are parts of the same bitmap (its top strip, bottom
  strip and lower-left tab), not separate art.
- `interface/quest_journal.swf` (Dear Diary) embeds 118 32x32/32x64 tiles (#1-#118, grey) and #350 (12x178), #355
  (687x1036, fully transparent); none is the frame. No DDS is drawn by these pages; imports are gfxfontlib,
  skyui/buttonArtDD.swf and skyui/ConfigPanel.swf (ConfigPanelFader) only.

## The run-time text colours (quest_journal.swf, Dear Diary 3.0.5; tag index in swf.read order, offset in tag data)

| tag | class | offset | value | use |
|---|---|---|---|---|
| 533 (DoInitAction) | Shared.BSScrollingList (SetEntryText) | +7675 | 0x000000 | row text, `enabled` branch (category list, left list, save list) |
| 533 | " | +7688 | 0x640000 | row text, other branch |
| 533 | " | +7746 | 0x000000 | row text, `disabled` branch |
| 533 | " | +7759 | 0x640000 | row text, other branch |
| 542 (DoInitAction) | QuestCenteredList.SetEntryText | +389 | 0x000000 | row text, `completed` branch |
| 542 | " | +402 | 0x053405 | row text, other branch |

Each is an ActionPush int32 feeding `textField.textColor` (SetMember); recolour_text only reaches DefineEditText
colours, so these stay black on the new dark ground.

## The restyle (install-time, tools/ui_theme/retheme.py; 0014)

- `JournalFramePalette` (palette.py) redraws the quest_journal BG sheet instead of recolouring it: the panels inside the
  wood band are found (integral-image box filter, connected parts on a 1/4 grid), each drawn as a straight rectangle on
  `frame-ground` at 0.95 alpha with a 2 px `frame-trim-hi` rule and a 1 px `frame-trim` inner rule; parts above the
  tallest panel (the header slot bars) are dropped; the button tab under the pane runs to the pane's right edge (the
  Load footer's Delete / Character Selection / Cancel overran its 370 px). The left list and the page merge into one
  pane (the divider's gap joins them), which matches 08's single pane. 0.16 s per sheet.
- `recolour_script_text` (retheme.py) finds every int32 an AS2 stream pushes as a `textColor` it sets and rewrites it
  in place: the six constants above; 0x640000 (dark red: the "Save" mark) to `frame-head`, the rest to `frame-text`.
- "Level 1" bar: the level text and meter are the movie's own fields and shapes (`LevelMeter_mc`), already in the frame
  tokens; its empty well was the sheet's bottom strip, now part of the pane.
- Contrast (WCAG 2, the menu loop's measure, on frame-ground composited at 0.95): frame-text 11.7:1, frame-head
  13.2:1, frame-text-soft 6.5:1; all above 4.5.

## L3 proof

`python -m tools.ui_theme.retheme --mods <dear-diary> <wood-and-paper> --out <t>` (73 files, 0 warnings), then
`python -m tools.ui_theme.frame_stills <t> <stills>` (rows now drawn in the movie's run-time colours). Reader on
settings.png and load.png against r5 still 08: "same family as 08, legible"; no cream or torn frame; all text light on
dark; header slot bars gone; the bottom strip wide enough for three buttons (the mock draws no buttons). The mock's
left labels sit at old sheet coordinates; in game the movie places them.

## Lockpicking (r5 21-lockpicking)

The step moved the crate by a world offset and pitched a fixed 20 degrees: the crosshair missed it, E hit nothing, no
lock opened (0 menu events). A new journey action `open: <ref>` (run_journey.py) reuses talk's face-and-aim with the
pitch set to a crate's middle (OPEN_Z 20, OPEN_UNITS 100), presses E only once the bridge's crosshair read holds the
crate, and retries E while no menu opens. menus-look's lockpicking step uses it on the locked Claywater crate.

## Owed

Two checks.md rows (1-core-loop): the Settings and Load pages in game, and the lockpicking step; the planner re-runs
menus-look on the next deploy (the theme overlay must be rebuilt by the installer to carry this).

## Second pass (r5 16:03 in game: dark text, translucent ground)

- Route 1 (config): Dear Diary's `fJournalAlpha = 100` already (deardiary/config.txt:185); SkyUI's `colors.text.*`
  (skyui/config.txt:44-49) colour SkyUI's item lists, not the Journal's System page. No config reaches these pages.
- Every text colour in quest_journal.swf, enumerated: 53 DefineEditText TextColors; their initial HTML
  `<font color>` attributes (ffffff x27, 000000 x9, aaaaaa, 999999, 666666, cccccc, dddddd x2 each), which override the
  field colour and were the black category list, date line, Level and button labels; the six SetEntryText pushes
  above; tag 557 +1598 0xaaaaaa (`defaultTextFormat.color`); tag 539 +1157 0xff0000 is a filter flag, not a colour.
- Fix (97fc35dc): the HTML colours and the TextFormat push go through the same frame-text map. Measured on the
  rebuilt overlay: the only text colours left in the movie are #d9cfa6 and #e6dcb2 (11.7:1 and 13.2:1).
- Ground: my redraw set 0.95 alpha; now 255 (the sheet's alpha values are exactly {0, 255}).
- Not done: the "Level 1" meter (LevelMeter_mc, the movie's own shapes) still shows; hiding it needs its placement
  edited. The header band is already gone in the 16:03 stills.

## Third pass (r5 17:06: list rows, Level, footer labels still black)

Route B (route A, Dear Diary's dark edition, needs a new download and permissions; B was one function). The cause is
neither a field colour nor a push: Dear Diary blacks its text with colour transforms on the placed clips (PlaceObject2
CXFORM, red/green/blue multipliers 0, e.g. sprite 153 placing fields 140-152, sprites 124, 128, 169, 182, 188), so
the cream colours were multiplied to black. `unblack_text` (retheme.py) finds every placement of a text field, or of a
clip that holds one, whose transform darkens (all colour multipliers below 1.0, no positive add) and sets red, green
and blue to 1.0, alpha kept. Measured on the rebuilt overlay: 40 lifted in quest_journal.swf, 22, 10 and 8 in the
other frame movies (config panel, message box, lockpicking); a second pass finds 0; the darkening transforms left are
on shapes and icon clips (no text). Not done: the B/X/Y glyph art (skyui/buttonArtDD.swf) is shared with the paper
menus and keeps the light palette.
